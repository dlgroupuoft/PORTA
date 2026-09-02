// Copyright 2023 The Casdoor Authors. All Rights Reserved.
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
type ValidatorFunc func(password string, lang string) string
func isValidOption_AtLeast6(password string, lang string) string {
func isValidOption_AtLeast8(password string, lang string) string {
func isValidOption_Aa123(password string, lang string) string {
func isValidOption_SpecialChar(password string, lang string) string {
func isValidOption_NoRepeat(password string, lang string) string {
func checkPasswordComplexity(password string, options []string, lang string) string {
// CheckPasswordNotSameAsCurrent checks if the new password is different from the current password
func CheckPasswordNotSameAsCurrent(user *User, newPassword string, organization *Organization) bool {
		// User doesn't have a password set (e.g., OAuth-only users), allow any password
		// If no credential manager is available, we can't compare passwords
	// Check if the new password is the same as the current password
	// Try with both organization salt and user salt (like CheckPassword function does)