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
// GetTokens
// @Title GetTokens
// @Tag Token API
// @Description get tokens
// @Param   owner     query    string  true        "The organization name (e.g., built-in)"
// @Param   pageSize     query    string  true        "The size of each page"
// @Param   p     query    string  true        "The number of the page"
// @Success 200 {array} object.Token The Response object
// @router /get-tokens [get]
func (c *ApiController) GetTokens() {
// GetToken
// @Title GetToken
// @Tag Token API
// @Description get token
// @Param   id     query    string  true        "The token ID in format: organization/token-name (e.g., built-in/token-123456)"
// @Success 200 {object} object.Token The Response object
// @router /get-token [get]
func (c *ApiController) GetToken() {
// UpdateToken
// @Title UpdateToken
// @Tag Token API
// @Description update token
// @Param   id     query    string  true        "The token ID in format: organization/token-name (e.g., built-in/token-123456)"
// @Param   body    body   object.Token  true        "Details of the token"
// @Success 200 {object} controllers.Response The Response object
// @router /update-token [post]
func (c *ApiController) UpdateToken() {
// AddToken
// @Title AddToken
// @Tag Token API
// @Description add token
// @Param   body    body   object.Token  true        "Details of the token"
// @Success 200 {object} controllers.Response The Response object
// @router /add-token [post]
func (c *ApiController) AddToken() {
// DeleteToken
// @Tag Token API
// @Title DeleteToken
// @Description delete token
// @Param   body    body   object.Token  true        "Details of the token"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-token [post]
func (c *ApiController) DeleteToken() {
// GetOAuthToken
// @Title GetOAuthToken
// @Tag Token API
// @Description get OAuth access token
// @Param   grant_type     query    string  true        "OAuth grant type"
// @Param   client_id     query    string  true        "OAuth client id"
// @Param   client_secret     query    string  true        "OAuth client secret"
// @Param   code     query    string  true        "OAuth code"
// @Success 200 {object} object.TokenWrapper The Response object
// @Success 400 {object} object.TokenError The Response object
// @Success 401 {object} object.TokenError The Response object
// @router /login/oauth/access_token [post]
func (c *ApiController) GetOAuthToken() {
		// If clientId is empty, try to read data from RequestBody
// RefreshToken
// @Title RefreshToken
// @Tag Token API
// @Description refresh OAuth access token
// @Param   grant_type     query    string  true        "OAuth grant type"
// @Param	refresh_token	query	string	true		"OAuth refresh token"
// @Param   scope     query    string  true        "OAuth scope"
// @Param   client_id     query    string  true        "OAuth client id"
// @Param   client_secret     query    string  false        "OAuth client secret"
// @Success 200 {object} object.TokenWrapper The Response object
// @Success 400 {object} object.TokenError The Response object
// @Success 401 {object} object.TokenError The Response object
// @router /login/oauth/refresh_token [post]
func (c *ApiController) RefreshToken() {
		// If clientID is empty, try to read data from RequestBody
func (c *ApiController) ResponseTokenError(errorMsg string, errorDescription string) {
func (c *ApiController) ValidateOAuth(ignoreValidSecret bool) (ok bool, application *object.Application, clientId, clientSecret string, err error) {
// IntrospectToken
// @Title IntrospectToken
// @Tag Login API
// @Description The introspection endpoint is an OAuth 2.0 endpoint that takes a
// parameter representing an OAuth 2.0 token and returns a JSON document
// representing the meta information surrounding the
// token, including whether this token is currently active.
// This endpoint support Basic Authorization and authorization defined in RFC 7523.
//
// @Param token formData string true "access_token's value or refresh_token's value"
// @Param token_type_hint formData string true "the token type access_token or refresh_token"
// @Success 200 {object} object.IntrospectionResponse The Response object
// @Success 400 {object} object.TokenError The Response object
// @Success 401 {object} object.TokenError The Response object
// @router /login/oauth/introspect [post]
func (c *ApiController) IntrospectToken() {
			// and token revoked case. but we not implement
			// TODO: 2022-03-03 add token revoked check, when we implemented the Token Revocation(rfc7009) Specs.
			// refs: https://tools.ietf.org/html/rfc7009
			// and token revoked case. but we not implement
			// TODO: 2022-03-03 add token revoked check, when we implemented the Token Revocation(rfc7009) Specs.
			// refs: https://tools.ietf.org/html/rfc7009