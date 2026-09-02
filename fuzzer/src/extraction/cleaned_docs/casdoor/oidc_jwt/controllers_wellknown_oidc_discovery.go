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
package controllers
// GetOidcDiscovery
// @Title GetOidcDiscovery
// @Tag OIDC API
// @Description Get Oidc Discovery
// @Success 200 {object} object.OidcDiscovery
// @router /.well-known/openid-configuration [get]
func (c *RootController) GetOidcDiscovery() {
// GetOidcDiscoveryByApplication
// @Title GetOidcDiscoveryByApplication
// @Tag OIDC API
// @Description Get Oidc Discovery for specific application
// @Param application path string true "application name"
// @Success 200 {object} object.OidcDiscovery
// @router /.well-known/:application/openid-configuration [get]
func (c *RootController) GetOidcDiscoveryByApplication() {
// GetJwks
// @Title GetJwks
// @Tag OIDC API
// @Success 200 {object} jose.JSONWebKey
// @router /.well-known/jwks [get]
func (c *RootController) GetJwks() {
// GetJwksByApplication
// @Title GetJwksByApplication
// @Tag OIDC API
// @Param application path string true "application name"
// @Success 200 {object} jose.JSONWebKey
// @router /.well-known/:application/jwks [get]
func (c *RootController) GetJwksByApplication() {
// GetWebFinger
// @Title GetWebFinger
// @Tag OIDC API
// @Param resource query string true "resource"
// @Success 200 {object} object.WebFinger
// @router /.well-known/webfinger [get]
func (c *RootController) GetWebFinger() {
// GetWebFingerByApplication
// @Title GetWebFingerByApplication
// @Tag OIDC API
// @Param application path string true "application name"
// @Param resource query string true "resource"
// @Success 200 {object} object.WebFinger
// @router /.well-known/:application/webfinger [get]
func (c *RootController) GetWebFingerByApplication() {
// GetOAuthServerMetadata
// @Title GetOAuthServerMetadata
// @Tag OAuth API
// @Description Get OAuth 2.0 Authorization Server Metadata (RFC 8414)
// @Success 200 {object} object.OidcDiscovery
// @router /.well-known/oauth-authorization-server [get]
func (c *RootController) GetOAuthServerMetadata() {
// GetOAuthServerMetadataByApplication
// @Title GetOAuthServerMetadataByApplication
// @Tag OAuth API
// @Description Get OAuth 2.0 Authorization Server Metadata for specific application (RFC 8414)
// @Param application path string true "application name"
// @Success 200 {object} object.OidcDiscovery
// @router /.well-known/:application/oauth-authorization-server [get]
func (c *RootController) GetOAuthServerMetadataByApplication() {