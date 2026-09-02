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
func init() {
func isValidRealName(s string) bool {
func resetUserSigninErrorTimes(user *User) error {
	// if the password is correct and wrong times is not zero, reset the error times
func GetFailedSigninConfigByUser(user *User) (int, int, error) {
func recordSigninErrorInfo(user *User, lang string, options ...bool) error {
	// increase failed login count
		// record the latest failed login time
	// update user
	// don't show the chance error message if the user has no chance left