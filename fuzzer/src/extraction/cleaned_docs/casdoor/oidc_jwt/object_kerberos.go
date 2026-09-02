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
// ctxCredentials is the SPNEGO context key holding the Kerberos credentials.
// This must match the value used internally by gokrb5's spnego package.
// If the gokrb5 library changes this internal constant in a future version,
// this value will need to be updated accordingly.
// ValidateKerberosToken validates a base64-encoded SPNEGO token from the
// Authorization header and returns the authenticated Kerberos username.
func ValidateKerberosToken(organization *Organization, spnegoTokenBase64 string) (string, error) {
// GetUserByKerberosName looks up a Casdoor user by their Kerberos principal name.
// It strips the realm part (e.g., "user@REALM.COM" -> "user") and searches by username.
func GetUserByKerberosName(organizationName string, kerberosUsername string) (*User, error) {