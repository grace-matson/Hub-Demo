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

import java.util.List;
import java.util.Objects;

/**
 * An action specification.
 */
public class ActionSpec implements Validatable {
  private final String type;
  private final String label;
  private final List<ActionArguments> arguments;

  public ActionSpec(String type, String label, List<ActionArguments> arguments) {
    this.type = type;
    this.label = label;
    this.arguments = arguments;
  }

  public String getType() {
    return type;
  }

  public String getLabel() {
    return label;
  }

  public List<ActionArguments> getArguments() {
    return arguments;
  }

  @Override
  public void validate() {
    if (type == null || type.isEmpty()) {
      throw new IllegalArgumentException("Action type must be specified.");
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

    ActionSpec that = (ActionSpec) o;
    return Objects.equals(type, that.type) &&
      Objects.equals(label, that.label) &&
      Objects.equals(arguments, that.arguments);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, label, arguments);
  }

  @Override
  public String toString() {
    return "ActionSpec{" +
      "type='" + type + '\'' +
      ", label='" + label + '\'' +
      ", arguments=" + arguments +
      '}';
  }
}
