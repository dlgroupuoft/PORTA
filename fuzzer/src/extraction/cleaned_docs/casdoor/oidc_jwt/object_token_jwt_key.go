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
func generateRsaKeys(bitSize int, shaSize int, expireInYears int, commonName string, organization string) (string, string, error) {
	// https://stackoverflow.com/questions/64104586/use-golang-to-get-rsa-key-the-same-way-openssl-genrsa
	// https://stackoverflow.com/questions/43822945/golang-can-i-create-x509keypair-using-rsa-key
	// Generate RSA key.
	// Encode private key to PKCS#1 ASN.1 PEM.
		// you can add any attr that you need
		// you have to generate a different serial number each execution
	// Generate a pem block with the certificate
func generateEsKeys(shaSize int, expireInYears int, commonName string, organization string) (string, string, error) {
	// Generate ECDSA key pair.
	// Encode private key to PEM format.
	// Generate certificate template.
	// Generate certificate.
	// Encode certificate to PEM format.
func generateRsaPssKeys(bitSize int, shaSize int, expireInYears int, commonName string, organization string) (string, string, error) {
	// Generate RSA key.
	// Encode private key to PKCS#8 ASN.1 PEM.
		// you can add any attr that you need
		// you have to generate a different serial number each execution
	// Set the signature algorithm based on the hash function
	// Generate a pem block with the certificate