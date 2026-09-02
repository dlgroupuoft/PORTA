// Copyright 2026 The Casdoor Authors. All Rights Reserved.
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
// ConsentRecord represents the data for OAuth consent API requests/responses
type ConsentRecord struct {
	// owner/name
// ScopeDescription represents a human-readable description of an OAuth scope
type ScopeDescription struct {
// parseScopes converts a space-separated scope string to a slice
func parseScopes(scopeStr string) []string {
// CheckConsentRequired checks if user consent is required for the OAuth flow
func CheckConsentRequired(userObj *User, application *Application, scopeStr string) (bool, error) {
	// Skip consent when no custom scopes are configured
	// Once policy: check if consent already granted
	// Filter requestedScopes to only include scopes defined in application.CustomScopes
	// If no valid requested scopes, no consent required
			// Check if grantedScopes contains all validRequestedScopes
				// Consent already granted for all valid requested scopes
	// Consent required
func validateCustomScopes(customScopes []*ScopeDescription, lang string) error {