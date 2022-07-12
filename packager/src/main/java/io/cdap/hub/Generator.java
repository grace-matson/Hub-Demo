/*
 * Copyright © 2016 Cask Data, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package io.cdap.hub;

import com.google.common.base.Splitter;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import io.cdap.hub.spec.ActionArguments;
import io.cdap.hub.spec.ActionSpec;
import io.cdap.hub.spec.PackageSpec;
import org.apache.commons.cli.BasicParser;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Reader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import javax.annotation.Nullable;

/**
 * Tool used to generate new packages from existing ones, or modify existing packages.
 */
public class Generator {
  private static final Logger LOG = LoggerFactory.getLogger(Generator.class);
  private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().setPrettyPrinting().create();
  private static final Set<String> PIPELINE_ACTIONS = ImmutableSet.of("create_pipeline", "create_pipeline_draft");
  private final File packagesDir;
  private final String cdapVersion;
  private final String pluginVersion;
  private final String packageVersion;
  private final boolean includeBeta;
  private final Set<String> categories;
  private final long timestamp;

  public Generator(File packagesDir, String cdapVersion, String packageVersion,
                   @Nullable String pluginVersion, boolean includeBeta, Set<String> categories) {
    this.packagesDir = packagesDir;
    this.includeBeta = includeBeta;
    this.cdapVersion = cdapVersion;
    this.pluginVersion = pluginVersion;
    this.packageVersion = packageVersion;
    this.categories = categories;
    this.timestamp = System.currentTimeMillis() / 1000L;
  }

  public void generate(final String baseVersion) throws IOException {
    walkPackages(new PackageOp() {
      @Override
      public void op(File versionDir, PackageSpec spec, List<File> resources) throws IOException {
        if (!versionDir.getName().equals(baseVersion)) {
          return;
        }

        LOG.info("generating new package version {} from {}", packageVersion, versionDir);
        PackageSpec newSpec = modifySpec(spec);

        File newPackageDir = new File(versionDir.getParentFile(), packageVersion);
        // if the new package dir already exists, error out
        if (newPackageDir.exists()) {
          throw new IllegalStateException("New package directory " + newPackageDir + " already exists!");
        }

        // create new package dir
        if (!newPackageDir.mkdir()) {
          throw new IOException("Failed to create new package directory " + newPackageDir);
        }

        File specFile = new File(newPackageDir, "spec.json");
        LOG.info("writing new spec {}", specFile);
        try (FileWriter fileWriter = new FileWriter(specFile)) {
          GSON.toJson(newSpec, PackageSpec.class, fileWriter);
        }

        // copy all resources, modifying anything that is a pipeline config.
        Set<String> configs = getAppConfigs(spec);
        for (File resource : resources) {
          File newFile = new File(newPackageDir, resource.getName());
          if (configs.contains(resource.getName())) {
            LOG.info("copying and modifying {}", resource.getName());
            try (FileReader reader = new FileReader(resource);
              FileWriter writer = new FileWriter(newFile)) {
              GSON.toJson(modifyHydratorConfig(GSON.fromJson(reader, JsonObject.class)), writer);
            }
          } else {
            LOG.info("copying {}", resource.getName());
            Files.copy(resource, newFile);
          }
        }
      }
    });
  }

  public void modify() throws IOException {
    walkPackages(new PackageOp() {
      @Override
      public void op(File versionDir, PackageSpec spec, List<File> resources) throws IOException {
        if (!versionDir.getName().equals(packageVersion)) {
          return;
        }
        LOG.info("modifying package at {}", versionDir);

        File specFile = new File(versionDir, "spec.json");
        LOG.info("modifying spec");
        PackageSpec newSpec = modifySpec(spec);
        try (FileWriter fileWriter = new FileWriter(specFile)) {
          GSON.toJson(newSpec, PackageSpec.class, fileWriter);
        }

        // modify anything that is a pipeline config.
        for (String config : getAppConfigs(spec)) {
          LOG.info("modifying {}", config);
          try (FileReader reader = new FileReader(new File(versionDir, config))) {
            JsonObject newConfig = modifyHydratorConfig(GSON.fromJson(reader, JsonObject.class));
            try (FileWriter writer = new FileWriter(new File(versionDir, config))) {
              GSON.toJson(newConfig, writer);
            }
          }
        }
      }
    });
  }

  @SuppressWarnings("ConstantConditions")
  public void walkPackages(PackageOp packageOp) throws IOException {
    for (File packageDir : packagesDir.listFiles()) {
      if (!packageDir.isDirectory()) {
        continue;
      }

      for (File versionDir : packageDir.listFiles()) {
        if (!versionDir.isDirectory()) {
          continue;
        }

        List<File> resources = new ArrayList<>();
        PackageSpec spec = null;
        for (File packagefile : versionDir.listFiles()) {
          if (packagefile.getName().equals("spec.json")) {
            try (Reader reader = new FileReader(packagefile)) {
              spec = GSON.fromJson(reader, PackageSpec.class);
              spec.validate();
            } catch (Exception e) {
              throw new IllegalArgumentException("Unable to parse spec file " + packagefile, e);
            }
          } else {
            resources.add(packagefile);
          }
        }

        if (spec == null || spec.getBeta() && !includeBeta) {
          continue;
        }

        for (String packageCategory : spec.getCategories()) {
          if (categories.contains(packageCategory)) {
            packageOp.op(versionDir, spec, resources);
          }
        }
      }
    }
  }

  // these configs hold a bunch of ui stuff, otherwise we could use the proto object in cdap-etl-proto
  private JsonObject modifyHydratorConfig(JsonObject config) {
    for (JsonElement stage : config.getAsJsonArray("stages")) {
      JsonObject pluginArtifact = stage.getAsJsonObject().getAsJsonObject("plugin").getAsJsonObject("artifact");
      pluginArtifact.addProperty("version", pluginVersion);
    }
    return config;
  }

  // create a new spec from an existing spec. Replaces create time, cdap version range, and artifact version
  // of any pipeline actions
  private PackageSpec modifySpec(PackageSpec oldSpec) {
    // replace cdap version in any create_pipeline or create_pipeline_draft actions
    List<ActionSpec> oldActions = oldSpec.getActions();
    List<ActionSpec> newActions = new ArrayList<>(oldActions.size());
    for (ActionSpec oldAction : oldActions) {
      if (PIPELINE_ACTIONS.contains(oldAction.getType())) {
        List<ActionArguments> newArguments = new ArrayList<>();
        for (ActionArguments argument : oldAction.getArguments()) {
          if ("artifact".equals(argument.getName())) {
            JsonObject oldArtifact = argument.getValue().getAsJsonObject();
            JsonObject newArtifact = new JsonObject();
            newArtifact.add("scope", oldArtifact.get("scope"));
            newArtifact.add("name", oldArtifact.get("name"));
            newArtifact.addProperty("version", cdapVersion);
            newArguments.add(new ActionArguments(argument.getName(), newArtifact, argument.getCanModify()));
            continue;
          }
          newArguments.add(argument);
        }
        newActions.add(new ActionSpec(oldAction.getType(), oldAction.getLabel(), newArguments));
        continue;
      }
      newActions.add(oldAction);
    }
    String cdapVersionRange = String.format("[%s,%s]", cdapVersion, cdapVersion);
    return new PackageSpec(oldSpec, cdapVersionRange, timestamp, newActions);
  }

  private Set<String> getAppConfigs(PackageSpec spec) {
    Set<String> configs = new HashSet<>();
    for (ActionSpec action : spec.getActions()) {
      if (!PIPELINE_ACTIONS.contains(action.getType())) {
        continue;
      }
      for (ActionArguments argument : action.getArguments()) {
        if ("config".equals(argument.getName())) {
          configs.add(argument.getValue().getAsString());
          break;
        }
      }
    }
    return configs;
  }

  /**
   * performs some operation on a package
   */
  private interface PackageOp {
    void op(File versionDir, PackageSpec spec, List<File> resources) throws IOException;
  }

  public static void main(String[] args) throws Exception {

    Options options = new Options()
      .addOption(new Option("h", "help", false, "Print this usage message."))
      .addOption(new Option("c", "categories", true,
                            "comma separated list of categories to generate new packages for."))
      .addOption(new Option("d", "dir", true,
                            "Directory containing packages. Defaults to the current working directory."))
      .addOption(new Option("b", "beta", false, "include beta packages."))
      .addOption(new Option("bv", "base-version", true, "package version to copy when generating a new package."))
      .addOption(new Option("pv", "package-version", true, "package version to generate or modify."))
      .addOption(new Option("cv", "cdap-version", true, "cdapVersion to use in package specs."))
      .addOption(new Option("gv", "plugin-version", true, "plugin version to use in hydrator pipeline configs."));

    CommandLineParser parser = new BasicParser();
    CommandLine commandLine = parser.parse(options, args);
    String[] commandArgs = commandLine.getArgs();

    // if help is an option
    if (commandLine.hasOption("h") || commandArgs.length == 0) {
      HelpFormatter helpFormatter = new HelpFormatter();
      helpFormatter.printHelp(
        Packager.class.getName() + " command",
        "supported commands are 'generate' and 'modify'.\n" +
          "'generate' will create a new package by copying the contents from the highest current package version.\n" +
          "'modify' will change the cdapVersion of package specs and plugin versions of any hydrator configs.\n",
        options, "");
      System.exit(0);
    }

    String command = commandArgs[0];
    if (!command.equalsIgnoreCase("generate") && !command.equalsIgnoreCase("modify")) {
      LOG.error("Unrecognized command '{}'. Command must be 'generate' or 'modify'", command);
      System.exit(1);
    }

    // read and validate options

    // get package directory
    String packageDirectoryStr = commandLine.hasOption("d") ?
      commandLine.getOptionValue("d") : System.getProperty("user.dir");

    File packagesDir = new File(packageDirectoryStr, "packages");
    if (!packagesDir.exists()) {
      LOG.error("Directory '{}' does not exist.", packagesDir);
      System.exit(1);
    }
    if (!packagesDir.isDirectory()) {
      LOG.error("Directory '{}' is not a directory.", packagesDir);
      System.exit(1);
    }

    boolean includeBeta = commandLine.hasOption("b");
    String cdapVersion = commandLine.getOptionValue("cv");
    if (cdapVersion == null) {
      LOG.error("must specify a cdap version.");
      System.exit(1);
    }
    String packageVersion = commandLine.getOptionValue("pv");
    if (packageVersion == null) {
      LOG.error("must specify a package version.");
      System.exit(1);
    }
    String pluginVersion = commandLine.getOptionValue("gv");
    String categoriesStr = commandLine.hasOption("c") ? commandLine.getOptionValue("c") : "pipeline,usecase";
    Set<String> categories = new HashSet<>();
    for (String category : Splitter.on(',').trimResults().split(categoriesStr)) {
      categories.add(category);
    }
    Generator generator = new Generator(packagesDir, cdapVersion, packageVersion,
                                        pluginVersion, includeBeta, categories);

    if (command.equals("generate")) {
      String baseVersion = commandLine.getOptionValue("bv");
      if (baseVersion == null) {
        LOG.error("must specify a base package version when generating new packages.");
        System.exit(1);
      }
      generator.generate(baseVersion);
    } else if (command.equals("modify")) {
      generator.modify();
    }
  }
}
