// Copyright 2024 The Casdoor Authors. All Rights Reserved.
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
type CLIVersionInfo struct {
// cleanOldMEIFolders cleans up old _MEIXXX folders from the Casdoor temp directory
// that are older than 24 hours. These folders are created by PyInstaller when
// executing casbin-python-cli and can accumulate over time.
func cleanOldMEIFolders() {
		// Log error but don't fail - cleanup is best-effort
		// This is expected if temp directory doesn't exist yet
		// Check if the entry is a directory and matches the _MEI pattern
		// Check if the folder is older than 24 hours
			// Try to remove the directory
				// Log but continue with other folders
// getCLIVersion
// @Title getCLIVersion
// @Description Get CLI version with cache mechanism
// @Param language string The language of CLI (go/java/rust etc.)
// @Return string The version string of CLI
// @Return error Error if CLI execution fails
func getCLIVersion(language string) (string, error) {
	// Clean up old _MEI folders before running the command
func processArgsToTempFiles(args []string) ([]string, []string, error) {
// RunCasbinCommand
// @Title RunCasbinCommand
// @Tag Enforcer API
// @Description Call Casbin CLI commands
// @Success 200 {object} controllers.Response The Response object
// @router /run-casbin-command [get]
func (c *ApiController) RunCasbinCommand() {
	// use "casbin-go-cli" by default, can be also "casbin-java-cli", "casbin-node-cli", etc.
	// the pre-built binary of "casbin-go-cli" can be found at: https://github.com/casbin/casbin-go-cli/releases
	// RBAC model & policy example:
	// https://door.casdoor.com/api/run-casbin-command?language=go&args=["enforce", "-m", "[request_definition]\nr = sub, obj, act\n\n[policy_definition]\np = sub, obj, act\n\n[role_definition]\ng = _, _\n\n[policy_effect]\ne = some(where (p.eft == allow))\n\n[matchers]\nm = g(r.sub, p.sub) %26%26 r.obj == p.obj %26%26 r.act == p.act", "-p", "p, alice, data1, read\np, bob, data2, write\np, data2_admin, data2, read\np, data2_admin, data2, write\ng, alice, data2_admin", "alice", "data1", "read"]
	// Casbin CLI usage:
	// https://github.com/jcasbin/casbin-java-cli?tab=readme-ov-file#get-started
	// Generate cache key for this command
	// Check if result is cached
	// Clean up old _MEI folders before running the command
	// This is especially important for Python CLI which creates these folders
	// Store result in cache
// validateIdentifier
// @Title validateIdentifier
// @Description Validate the request hash and timestamp
// @Param hash string The SHA-256 hash string
// @Return error Returns error if validation fails, nil if successful
func validateIdentifier(c *ApiController) error {