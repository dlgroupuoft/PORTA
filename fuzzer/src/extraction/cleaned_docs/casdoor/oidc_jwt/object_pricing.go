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
type Pricing struct {
func (pricing *Pricing) GetId() string {
func (pricing *Pricing) HasPlan(planName string, lang string) (bool, error) {
func GetPricingCount(owner, field, value string) (int64, error) {
func GetPricings(owner string) ([]*Pricing, error) {
func GetPaginatedPricings(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Pricing, error) {
func getPricing(owner, name string) (*Pricing, error) {
func GetPricing(id string) (*Pricing, error) {
func GetApplicationDefaultPricing(owner, appName string) (*Pricing, error) {
func UpdatePricing(id string, pricing *Pricing) (bool, error) {
func AddPricing(pricing *Pricing) (bool, error) {
func DeletePricing(pricing *Pricing) (bool, error) {
func CheckPricingAndPlan(owner, pricingName, planName string, lang string) error {