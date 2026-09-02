// Copyright 2023 The Casdoor Authors. All Rights Reserved.
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
type Enforcer struct {
func GetEnforcerCount(owner, field, value string) (int64, error) {
func GetEnforcers(owner string) ([]*Enforcer, error) {
func GetPaginationEnforcers(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Enforcer, error) {
func getEnforcer(owner string, name string) (*Enforcer, error) {
func GetEnforcer(id string) (*Enforcer, error) {
func UpdateEnforcer(id string, enforcer *Enforcer) (bool, error) {
func AddEnforcer(enforcer *Enforcer) (bool, error) {
func DeleteEnforcer(enforcer *Enforcer) (bool, error) {
func (enforcer *Enforcer) GetId() string {
func (enforcer *Enforcer) GetModelAndAdapter() string {
func (enforcer *Enforcer) InitEnforcer() error {
func GetInitializedEnforcer(enforcerId string) (*Enforcer, error) {
func GetPolicies(id string) ([]*xormadapter.CasbinRule, error) {
// Filter represents filter criteria with optional policy type
type Filter struct {
func GetFilteredPolicies(id string, ptype string, fieldIndex int, fieldValues ...string) ([]*xormadapter.CasbinRule, error) {
// GetFilteredPoliciesMulti applies multiple filters to policies
// Doing this in our loop is more efficient than using GetFilteredGroupingPolicy / GetFilteredPolicy which
// iterates over all policies again and again
func GetFilteredPoliciesMulti(id string, filters []Filter) ([]*xormadapter.CasbinRule, error) {
	// Get all policies first
	// Filter policies based on multiple criteria
		// No filters, return all policies
				// Default policy type if unspecified
				// Always check policy type
				// If FieldIndex is nil, only filter via ptype (skip field-value checks)
				// If FieldIndex is out of range, also only filter via ptype
				// When FieldIndex is provided and valid, enforce FieldValues (if any)
func UpdatePolicy(id string, ptype string, oldPolicy []string, newPolicy []string) (bool, error) {
func AddPolicy(id string, ptype string, policy []string) (bool, error) {
func RemovePolicy(id string, ptype string, policy []string) (bool, error) {
func (enforcer *Enforcer) LoadModelCfg() error {