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
// OriginalGroup represents a group from an external system
type OriginalGroup struct {
// SyncerProvider defines the interface that all syncer implementations must satisfy.
// Different syncer types (Database, Keycloak, WeCom, Azure AD) implement this interface.
type SyncerProvider interface {
	// InitAdapter initializes the connection to the external system
	// GetOriginalUsers retrieves all users from the external system
	// GetOriginalGroups retrieves all groups from the external system
	// GetOriginalUserGroups retrieves the group IDs that a user belongs to
	// AddUser adds a new user to the external system
	// UpdateUser updates an existing user in the external system
	// TestConnection tests the connection to the external system
	// Close closes any open connections and releases resources
// GetSyncerProvider returns the appropriate SyncerProvider implementation based on syncer type
func GetSyncerProvider(syncer *Syncer) SyncerProvider {
		// Default to database syncer for "Database" type and any others