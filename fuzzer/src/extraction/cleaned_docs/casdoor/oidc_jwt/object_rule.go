// Copyright 2023 The casbin Authors. All Rights Reserved.
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
type Expression struct {
type Rule struct {
func GetGlobalRules() ([]*Rule, error) {
func GetRules(owner string) ([]*Rule, error) {
func getRule(owner string, name string) (*Rule, error) {
func GetRule(id string) (*Rule, error) {
func UpdateRule(id string, rule *Rule) (bool, error) {
func AddRule(rule *Rule) (bool, error) {
func DeleteRule(rule *Rule) (bool, error) {
func (rule *Rule) GetId() string {
func GetRuleCount(owner, field, value string) (int64, error) {
func GetPaginationRules(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Rule, error) {