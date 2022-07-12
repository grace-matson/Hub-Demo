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

package io.cdap.hub.spec;

import java.io.File;
import javax.annotation.Nullable;

/**
 * Information about a category
 */
public class CategoryMeta {
  private final String name;
  private final boolean hasIcon;
  // don't want to serialize this
  private final transient File icon;

  public CategoryMeta(String name, @Nullable File icon) {
    this.name = name;
    this.icon = icon;
    this.hasIcon = icon != null;
  }

  public String getName() {
    return name;
  }

  public boolean hasIcon() {
    return hasIcon;
  }

  @Nullable
  public File getIcon() {
    return icon;
  }
}
