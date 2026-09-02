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
type PushMfa struct {
func (mfa *PushMfa) Initiate(userId string, issuer string) (*MfaProps, error) {
func (mfa *PushMfa) SetupVerify(passCode string) error {
	// For setup verification, send a test notification
	// Note: Full implementation would require a callback endpoint to receive approval/denial
	// from the mobile app, and passCode would contain the callback verification token
func (mfa *PushMfa) Enable(user *User) error {
func (mfa *PushMfa) Verify(passCode string) error {
	// Send the push notification for authentication
	// Note: Full implementation would require:
	// 1. A callback endpoint to receive approval/denial from the mobile app
	// 2. Persistent storage of challengeId to validate the callback
	// 3. passCode would contain the callback verification token
	// For now, this sends the notification and returns success to enable basic functionality
func (mfa *PushMfa) sendPushNotification(title string, message string) error {
		// Try to load provider if URL is set and we have database access
	// Generate a unique challenge ID for this notification
	// Note: In a full implementation, this would be stored in a cache/database
	// to validate callbacks from the mobile app
	// Get the notification provider
	// Send the push notification
	// Note: The challengeId is kept server-side and not exposed in the message
func NewPushMfaUtil(config *MfaProps) *PushMfa {
	// Load provider if URL is specified and ormer is initialized