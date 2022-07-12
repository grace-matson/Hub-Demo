/*
 * Copyright © 2018 Cask Data, Inc.
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

import io.cdap.hub.spec.CategoryMeta;

import java.io.File;
import java.util.List;

/**
 * Packages, categories, and catalogs for the Hub.
 */
public class Hub {
  private final List<Package> packages;
  private final List<CategoryMeta> categories;
  private final File packageCatalog;
  private final File categoryCatalog;

  public Hub(List<Package> packages, File packageCatalog, List<CategoryMeta> categories, File categoryCatalog) {
    this.packages = packages;
    this.packageCatalog = packageCatalog;
    this.categories = categories;
    this.categoryCatalog = categoryCatalog;
  }

  public List<Package> getPackages() {
    return packages;
  }

  public File getPackageCatalog() {
    return packageCatalog;
  }

  public List<CategoryMeta> getCategories() {
    return categories;
  }

  public File getCategoryCatalog() {
    return categoryCatalog;
  }
}
