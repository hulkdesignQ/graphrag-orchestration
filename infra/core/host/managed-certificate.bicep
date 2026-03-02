@description('Name of the Container Apps Environment')
param environmentName string

@description('Location for the certificate resource')
param location string = resourceGroup().location

@description('Custom domain name for the certificate (e.g., evidoc.hulkdesign.com)')
param domainName string

// Reference the existing Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: environmentName
}

// Managed certificate - Azure auto-provisions and renews TLS cert
// Prerequisites: CNAME record must point to the container app FQDN before deployment
resource managedCertificate 'Microsoft.App/managedEnvironments/managedCertificates@2024-10-02-preview' = {
  parent: containerAppsEnvironment
  name: 'cert-${replace(domainName, '.', '-')}'
  location: location
  properties: {
    subjectName: domainName
    domainControlValidation: 'CNAME'
  }
}

output certificateId string = managedCertificate.id
