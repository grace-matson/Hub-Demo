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

import com.google.gson.JsonElement;

import java.util.Objects;

/**
 * Arguments of an action.
 */
public class ActionArguments implements Validatable {
  private final String name;
  // this can anything. a string, a json object, a json array, etc.
  private final JsonElement value;
  private final Boolean canModify;

  // to make sure canModify is set to null if not specified during gson deserialization
  public ActionArguments() {
    this(null, null, false);
  }

  public ActionArguments(String name, JsonElement value, boolean canModify) {
    this.name = name;
    this.value = value;
    this.canModify = canModify;
  }

  public String getName() {
    return name;
  }

  public JsonElement getValue() {
    return value;
  }

  public Boolean getCanModify() {
    return canModify;
  }

  @Override
  public void validate() {
    if (name == null || name.isEmpty() || value == null) {
      throw new IllegalArgumentException("Action arguments must contain a name and a value.");
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

    ActionArguments that = (ActionArguments) o;
    return Objects.equals(name, that.name) && Objects.equals(value, that.value) && canModify == that.canModify;
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, value, canModify);
  }

  @Override
  public String toString() {
    return "ActionArguments{" +
      "name='" + name + '\'' +
      ", value='" + value + '\'' +
      ", canModify=" + canModify +
      '}';
  }
}
