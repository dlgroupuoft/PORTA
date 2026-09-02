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
// GetTickets
// @Title GetTickets
// @Tag Ticket API
// @Description get tickets
// @Param   owner     query    string  true        "The owner of tickets"
// @Success 200 {array} object.Ticket The Response object
// @router /get-tickets [get]
func (c *ApiController) GetTickets() {
			// For non-admin users, only show their own tickets
// GetTicket
// @Title GetTicket
// @Tag Ticket API
// @Description get ticket
// @Param   id     query    string  true        "The id ( owner/name ) of the ticket"
// @Success 200 {object} object.Ticket The Response object
// @router /get-ticket [get]
func (c *ApiController) GetTicket() {
	// Check permission: user can only view their own tickets unless they are admin
// UpdateTicket
// @Title UpdateTicket
// @Tag Ticket API
// @Description update ticket
// @Param   id     query    string  true        "The id ( owner/name ) of the ticket"
// @Param   body    body   object.Ticket  true        "The details of the ticket"
// @Success 200 {object} controllers.Response The Response object
// @router /update-ticket [post]
func (c *ApiController) UpdateTicket() {
	// Check permission
	// Normal users can only close their own tickets
		// Normal users can only change state to "Closed"
		// Preserve original fields that users shouldn't modify
// AddTicket
// @Title AddTicket
// @Tag Ticket API
// @Description add ticket
// @Param   body    body   object.Ticket  true        "The details of the ticket"
// @Success 200 {object} controllers.Response The Response object
// @router /add-ticket [post]
func (c *ApiController) AddTicket() {
	// Set the user field to the current user
// DeleteTicket
// @Title DeleteTicket
// @Tag Ticket API
// @Description delete ticket
// @Param   body    body   object.Ticket  true        "The details of the ticket"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-ticket [post]
func (c *ApiController) DeleteTicket() {
	// Only admins can delete tickets
// AddTicketMessage
// @Title AddTicketMessage
// @Tag Ticket API
// @Description add a message to a ticket
// @Param   id     query    string  true        "The id ( owner/name ) of the ticket"
// @Param   body    body   object.TicketMessage  true        "The message to add"
// @Success 200 {object} controllers.Response The Response object
// @router /add-ticket-message [post]
func (c *ApiController) AddTicketMessage() {
	// Check permission
	// Users can only add messages to their own tickets, admins can add to any ticket
	// Set the author and admin flag