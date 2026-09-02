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
// GetResources
// @Tag Resource API
// @Title GetResources
// @Description get resources
// @Param		owner 		query 		string 				true 				"Owner"
// @Param		user 		query 		string 				true 				"User"
// @Param 		pageSize 	query 		integer 			false 				"Page Size"
// @Param 		p 			query 		integer 				false 				"Page Number"
// @Param 		field 		query 		string 				false 				"Field"
// @Param 		value 		query 		string 				false 				"Value"
// @Param 		sortField 	query 		string 				false 				"Sort Field"
// @Param 		sortOrder 	query 		string 				false 				"Sort Order"
// @Success		200 		{array} 	object.Resource 	The Response object
// @router /get-resources [get]
func (c *ApiController) GetResources() {
// GetResource
// @Tag Resource API
// @Title GetResource
// @Description get resource
// @Param   	id			query   	string     			true        		"The id ( owner/name ) of resource"
// @Success 	200			{object}	object.Resource		The Response object
// @router /get-resource [get]
func (c *ApiController) GetResource() {
// UpdateResource
// @Tag Resource API
// @Title UpdateResource
// @Description get resource
// @Param   	id     		query   	string  			true				"The id ( owner/name ) of resource"
// @Param		resource	body		object.Resource		true				"The resource object"
// @Success 	200			{object}	controllers.Response					Success or error
// @router /update-resource [post]
func (c *ApiController) UpdateResource() {
// AddResource
// @Tag Resource API
// @Title AddResource
// @Param     	resource    body    	object.Resource  	true      			"Resource object"
// @Success 	200			{object}	controllers.Response					Success or error
// @router /add-resource [post]
func (c *ApiController) AddResource() {
// DeleteResource
// @Tag Resource API
// @Title DeleteResource
// @Param     	resource    body    	object.Resource  	true      			"Resource object"
// @Success 	200			{object}	controllers.Response					Success or error
// @router /delete-resource [post]
func (c *ApiController) DeleteResource() {
// UploadResource
// @Tag Resource API
// @Title UploadResource
// @Param     owner           query   	string    			true      			"Owner"
// @Param     user            query   	string    			true      			"User"
// @Param     application     query   	string    			true     			"Application"
// @Param     tag             query   	string    			false     			"Tag"
// @Param     parent          query   	string    			false     			"Parent"
// @Param     fullFilePath    query   	string    			true     			"Full File Path"
// @Param     createdTime     query   	string    			false     			"Created Time"
// @Param     description     query   	string    			false     			"Description"
// @Param     file            formData 	file      			true      			"Resource file"
// @Success   200             {object}  object.Resource  	FileUrl, objectKey
// @router /upload-resource [post]
func (c *ApiController) UploadResource() {
			// duplicated fullFilePath found, change it