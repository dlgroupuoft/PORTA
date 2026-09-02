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
func hasGravatar(client *http.Client, email string) (bool, error) {
	// Clean and lowercase the email
	// Generate MD5 hash of the email
	// Create Gravatar URL with d=404 parameter
	// Create context with 5 second timeout
	// Send a request to Gravatar
	// Check if the user has a custom Gravatar image
func getGravatarFileBuffer(client *http.Client, email string) (*bytes.Buffer, string, error) {
	// Clean and lowercase the email
	// Generate MD5 hash of the email
	// Create Gravatar URL