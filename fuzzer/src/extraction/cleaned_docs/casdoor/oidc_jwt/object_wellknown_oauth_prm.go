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
// OauthProtectedResourceMetadata represents RFC 9728 OAuth 2.0 Protected Resource Metadata
type OauthProtectedResourceMetadata struct {
// GetOauthProtectedResourceMetadata returns RFC 9728 Protected Resource Metadata for global discovery
func GetOauthProtectedResourceMetadata(host string) OauthProtectedResourceMetadata {
// GetOauthProtectedResourceMetadataByApplication returns RFC 9728 Protected Resource Metadata for application-specific discovery
func GetOauthProtectedResourceMetadataByApplication(host string, applicationName string) OauthProtectedResourceMetadata {
	// For application-specific discovery, the resource identifier includes the application name