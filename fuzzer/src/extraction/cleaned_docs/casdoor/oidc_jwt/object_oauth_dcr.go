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
// DynamicClientRegistrationRequest represents an RFC 7591 client registration request
type DynamicClientRegistrationRequest struct {
// DynamicClientRegistrationResponse represents an RFC 7591 client registration response
type DynamicClientRegistrationResponse struct {
// DcrError represents an RFC 7591 error response
type DcrError struct {
// RegisterDynamicClient creates a new application based on DCR request
func RegisterDynamicClient(req *DynamicClientRegistrationRequest, organization string) (*DynamicClientRegistrationResponse, *DcrError, error) {
	// Validate organization exists and has DCR enabled
	// Check if DCR is enabled for this organization
	// Validate required fields
	// Set defaults
	// Generate unique application name
	// Create Application object
	// Note: DCR applications are created under "admin" owner by default
	// This can be made configurable in future versions
	// Add the application
	// Build response