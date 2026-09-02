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
type LinkForm struct {
// Unlink ...
// @Tag Login API
// @Title Unlink
// @router /unlink [post]
// @Success 200 {object} object.Userinfo The Response object
func (c *ApiController) Unlink() {
	// the user will be unlinked from the provider
		// if the user is not the same as the one we are unlinking, we need to make sure the user is the global admin.
		// if the user is unlinking themselves, should check the provider can be unlinked, if not, we should return an error.
	// only two situations can happen here
	// 1. the user is the global admin
	// 2. the user is unlinking themselves and provider can be unlinked