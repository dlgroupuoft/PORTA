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
type RadiusMfa struct {
func (mfa *RadiusMfa) Initiate(userId string, issuer string) (*MfaProps, error) {
func (mfa *RadiusMfa) SetupVerify(passCode string) error {
func (mfa *RadiusMfa) Enable(user *User) error {
func (mfa *RadiusMfa) Verify(passCode string) error {
func (mfa *RadiusMfa) authenticateWithRadius(username, password string) error {
		// Try to load provider if URL is set and we have database access
	// Create RADIUS packet
	// Send request to RADIUS server
func NewRadiusMfaUtil(config *MfaProps) *RadiusMfa {
	// Load provider if URL is specified and ormer is initialized