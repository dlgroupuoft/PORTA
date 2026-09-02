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
type OriginalUser = User
func (syncer *Syncer) getOriginalUsers() ([]*OriginalUser, error) {
func (syncer *Syncer) addUser(user *OriginalUser) (bool, error) {
func (syncer *Syncer) getCasdoorColumns() []string {
func (syncer *Syncer) updateUser(user *OriginalUser) (bool, error) {
func (syncer *Syncer) updateUserForOriginalFields(user *User, key string) (bool, error) {
	// Skip password-related columns when the incoming user has no password data.
	// API-based syncers (DingTalk, WeCom, Lark, etc.) do not provide passwords,
	// so updating these columns would wipe out locally set passwords.
	// Add provider-specific field for API-based syncers to enable login binding
	// This allows synced users to login via their provider accounts
func (syncer *Syncer) calculateHash(user *OriginalUser) string {
func (syncer *Syncer) initAdapter() error {
func RunSyncUsersJob() {