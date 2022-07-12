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

package io.cdap.hub.spec;

import com.google.common.base.Strings;

import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * A package specification.
 */
public class PackageSpec implements Validatable {

  private final String specVersion;
  private final String description;
  private final String label;
  private final String author;
  private final String org;
  private final String cdapVersion;
  private final String license;
  private final LicenseInfo licenseInfo;
  private final long created;
  private final Boolean beta;
  private final Boolean preview;
  private final Set<String> categories;
  private final List<ActionSpec> actions;
  private final String paidLink;

  public PackageSpec(String specVersion, String description, String label, String author, String org,
                     String cdapVersion, String license, LicenseInfo licenseInfo, long created,
                     Boolean beta, Boolean preview, Set<String> categories, List<ActionSpec> actions,
                     String paidLink) {
    this.specVersion = specVersion;
    this.description = description;
    this.label = label;
    this.author = author;
    this.org = org;
    this.cdapVersion = cdapVersion;
    this.created = created;
    this.categories = categories;
    this.actions = actions;
    this.license = license;
    this.licenseInfo = licenseInfo;
    this.beta = beta;
    this.preview = preview;
    this.paidLink = paidLink;
  }


  public PackageSpec(PackageSpec oldSpec, String newCdapVersion, long newCreated, List<ActionSpec> newActions) {
    this(oldSpec.specVersion, oldSpec.description, oldSpec.label, oldSpec.author, oldSpec.org, newCdapVersion,
         oldSpec.license, oldSpec.licenseInfo, newCreated, oldSpec.beta, oldSpec.preview, oldSpec.categories,
         newActions, oldSpec.paidLink);
  }

  public String getPaidLink() {
    return paidLink;
  }

  public String getSpecVersion() {
    return specVersion;
  }

  public String getDescription() {
    return description;
  }

  public String getLabel() {
    return label;
  }

  public String getAuthor() {
    return author;
  }

  public String getOrg() {
    return org;
  }

  public String getCdapVersion() {
    return cdapVersion;
  }

  public String getLicense() {
    return license;
  }

  public LicenseInfo getLicenseInfo() {
    return licenseInfo;
  }

  public long getCreated() {
    return created;
  }

  public Boolean getBeta() {
    Boolean b = beta == null ? false : beta;
    Boolean p = preview == null ? false : preview;
    return b || p;
  }

  public Set<String> getCategories() {
    return categories;
  }

  public List<ActionSpec> getActions() {
    return actions;
  }

  public Boolean getPaid() {
    return !Strings.isNullOrEmpty(paidLink);
  }

  @Override
  public void validate() {
    for (ActionSpec actionSpec : actions) {
      actionSpec.validate();
    }
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }

    PackageSpec that = (PackageSpec) o;

    return Objects.equals(specVersion, that.specVersion) &&
      Objects.equals(description, that.description) &&
      Objects.equals(label, that.label) &&
      Objects.equals(author, that.author) &&
      Objects.equals(org, that.org) &&
      Objects.equals(cdapVersion, that.cdapVersion) &&
      Objects.equals(created, that.created) &&
      Objects.equals(categories, that.categories) &&
      Objects.equals(actions, that.actions);
  }

  @Override
  public int hashCode() {
    return Objects.hash(specVersion, description, label, author, org, cdapVersion, created, categories, actions);
  }

  @Override
  public String toString() {
    return "PackageSpec{" +
      "specVersion='" + specVersion + '\'' +
      ", description='" + description + '\'' +
      ", label='" + label + '\'' +
      ", author='" + author + '\'' +
      ", org='" + org + '\'' +
      ", cdapVersion='" + cdapVersion + '\'' +
      ", created=" + created +
      ", categories=" + categories +
      ", actions=" + actions +
      '}';
  }
}
