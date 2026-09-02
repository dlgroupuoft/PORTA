// Copyright 2021 The Casdoor Authors. All Rights Reserved.
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
type OidcDiscovery struct {
type WebFinger struct {
type WebFingerLink struct {
func isIpAddress(host string) bool {
	// Attempt to split the host and port, ignoring the error
		// If an error occurs, it might be because there's no port
		// In that case, use the original host string
	// Attempt to parse the host as an IP address (both IPv4 and IPv6)
	// if host is not nil is an IP address else is not an IP address
func getOriginFromHostInternal(host string) (string, string) {
	// "door.casdoor.com"
		// "localhost:8000" or "computer-name:80"
		// "192.168.0.10"
func getOriginFromHost(host string) (string, string) {
func GetOidcDiscovery(host string, applicationName string) OidcDiscovery {
	// If application is provided, use application-specific URLs
		// Application-specific issuer and endpoints (owner is always "admin")
		// Default global issuer and endpoints
	// Default OIDC scopes
	// Merge application-specific custom scopes if application is provided
				// Add custom scope names to the scopes list
	// Examples:
	// https://login.okta.com/.well-known/openid-configuration
	// https://auth0.auth0.com/.well-known/openid-configuration
	// https://accounts.google.com/.well-known/openid-configuration
	// https://access.line.me/.well-known/openid-configuration
func GetJsonWebKeySet(applicationName string) (jose.JSONWebKeySet, error) {
	// Get certs - use application-specific cert if applicationName is provided
		// Try to get application-specific cert (owner is always "admin")
	// Fallback to global certs if no application-specific cert found
	// follows the protocol rfc 7517(draft)
	// link here: https://self-issued.info/docs/draft-ietf-jose-json-web-key.html
	// or https://datatracker.ietf.org/doc/html/draft-ietf-jose-json-web-key
func GetWebFinger(resource string, rels []string, host string, applicationName string) (WebFinger, error) {
func GetDeviceAuthResponse(deviceCode string, userCode string, host string) DeviceAuthResponse {