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
func init() {
func getProviderEndpoint(provider *Provider) string {
func escapePath(path string) string {
func GetTruncatedPath(provider *Provider, fullFilePath string, limit int) string {
func GetUploadFileUrl(provider *Provider, fullFilePath string, hasTimestamp bool) (string, string) {
		// provider.Domain = "https://cdn.casbin.com/casdoor/"
		// provider.Domain = "http://localhost:8000" or "https://door.casdoor.com"
		// fileUrl = util.UrlJoin(host, escapePath(objectKey))
	// if fileUrl != "" && hasTimestamp {
	//	fileUrl = fmt.Sprintf("%s?t=%s", fileUrl, util.GetCurrentUnixTime())
	// }
func getStorageProvider(provider *Provider, lang string) (oss.StorageInterface, error) {
func uploadFile(provider *Provider, fullFilePath string, fileBuffer *bytes.Buffer, lang string) (string, string, error) {
func UploadFileSafe(provider *Provider, fullFilePath string, fileBuffer *bytes.Buffer, lang string) (string, string, error) {
	// check fullFilePath is there security issue
func DeleteFile(provider *Provider, objectKey string, lang string) error {
	// check fullFilePath is there security issue
func refineObjectKey(provider *Provider, objectKey string) string {