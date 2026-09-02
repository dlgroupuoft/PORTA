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
type Credential struct {
// Helper function to unmarshal JSON string into a target interface
func unmarshalJSON(value string, target interface{}) error {
// Helper function to marshal data to JSON string
func marshalToJSONString(data interface{}) string {
	// Check if the value is valid and can be nil
	// Check if it's a nillable type (pointer, slice, map, channel, function, interface) and is nil
	// Check if it's a slice and if so, check if it's empty
	// Return empty string for empty slices to indicate "no data" for syncer purposes
func (syncer *Syncer) getFullAvatarUrl(avatar string) string {
func (syncer *Syncer) getPartialAvatarUrl(avatar string) string {
func (syncer *Syncer) createUserFromOriginalUser(originalUser *OriginalUser, affiliationMap map[int]string) *User {
func (syncer *Syncer) createOriginalUserFromUser(user *User) *OriginalUser {
func (syncer *Syncer) setUserByKeyValue(user *User, key string, value string) {
func (syncer *Syncer) getUserValue(user *User, key string) string {
func (syncer *Syncer) getOriginalUsersFromMap(results []map[string]sql.NullString) []*OriginalUser {
			// query and set password and password salt from credential table
			// query and set signup application from user group table
			// create time
			// enable
func (syncer *Syncer) getMapFromOriginalUser(user *OriginalUser) map[string]string {
func (syncer *Syncer) getSqlSetStringFromMap(m map[string]string) string {