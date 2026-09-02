// Copyright 2021 The Casdoor Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
package object
func calculateHash(user *User) (string, error) {
func (user *User) UpdateUserHash() error {
func (user *User) UpdateUserPassword(organization *Organization) {
	// Don't hash empty passwords (e.g., for OAuth users)
		// Use organization salt if available, otherwise generate a random salt for the user