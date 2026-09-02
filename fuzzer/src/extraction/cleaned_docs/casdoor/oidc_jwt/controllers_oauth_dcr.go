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
package controllers
// DynamicClientRegister
// @Title DynamicClientRegister
// @Tag OAuth API
// @Description Register a new OAuth 2.0 client dynamically (RFC 7591)
// @Param   organization     query    string  false        "The organization name (defaults to built-in)"
// @Param   body    body   object.DynamicClientRegistrationRequest  true        "Client registration request"
// @Success 201 {object} object.DynamicClientRegistrationResponse
// @Failure 400 {object} object.DcrError
// @router /api/oauth/register [post]
func (c *ApiController) DynamicClientRegister() {
	// Get organization from query parameter or default to built-in
	// Register the client
	// Return 201 Created