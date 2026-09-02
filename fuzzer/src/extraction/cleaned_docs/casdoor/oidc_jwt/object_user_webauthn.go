// Copyright 2022 The casbin Authors. All Rights Reserved.
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
func GetWebAuthnObject(host string) (*webauthn.WebAuthn, error) {
		// RPIcon:     "https://duo.com/logo.png",           // Optional icon URL for your site
// WebAuthnID
// implementation of webauthn.User interface
func (user *User) WebAuthnID() []byte {
func (user *User) WebAuthnName() string {
func (user *User) WebAuthnDisplayName() string {
func (user *User) WebAuthnCredentials() []webauthn.Credential {
func (user *User) WebAuthnIcon() string {
// CredentialExcludeList returns a CredentialDescriptor array filled with all the user's credentials
func (user *User) CredentialExcludeList() []protocol.CredentialDescriptor {
func (user *User) AddCredentials(credential webauthn.Credential, isGlobalAdmin bool) (bool, error) {
func (user *User) DeleteCredentials(credentialIdBase64 string) (bool, error) {