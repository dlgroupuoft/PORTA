// Copyright 2025 The Casdoor Authors. All Rights Reserved.
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
// DatabaseSyncerProvider implements SyncerProvider for database-based syncers
type DatabaseSyncerProvider struct {
// InitAdapter initializes the database adapter
func (p *DatabaseSyncerProvider) InitAdapter() error {
		// Store SSH client for proper cleanup
// GetOriginalUsers retrieves all users from the database
func (p *DatabaseSyncerProvider) GetOriginalUsers() ([]*OriginalUser, error) {
	// Memory leak problem handling
	// https://github.com/casdoor/casdoor/issues/1256
	// Clear map contents to help garbage collection
// AddUser adds a new user to the database
func (p *DatabaseSyncerProvider) AddUser(user *OriginalUser) (bool, error) {
// UpdateUser updates an existing user in the database
func (p *DatabaseSyncerProvider) UpdateUser(user *OriginalUser) (bool, error) {
// TestConnection tests the database connection
func (p *DatabaseSyncerProvider) TestConnection() error {
// Close closes the database connection and SSH tunnel
func (p *DatabaseSyncerProvider) Close() error {
type dsnConnector struct {
func (t dsnConnector) Connect(ctx context.Context) (driver.Conn, error) {
func (t dsnConnector) Driver() driver.Driver {
// GetOriginalGroups retrieves all groups from Database (not implemented yet)
func (p *DatabaseSyncerProvider) GetOriginalGroups() ([]*OriginalGroup, error) {
	// TODO: Implement Database group sync
// GetOriginalUserGroups retrieves the group IDs that a user belongs to (not implemented yet)
func (p *DatabaseSyncerProvider) GetOriginalUserGroups(userId string) ([]string, error) {
	// TODO: Implement Database user group membership sync