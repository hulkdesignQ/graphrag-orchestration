// Azure Static Web App for the Evidoc marketing website
// Deploys a free-tier static site with global CDN and managed SSL

param name string
param location string = 'eastus2' // SWA has limited region support
param tags object = {}
param customDomainName string = ''

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    buildProperties: {
      appLocation: 'frontend/website'
      outputLocation: 'dist'
      skipGithubActionWorkflowGeneration: true
    }
  }
}

// Custom domain (e.g., evidoc.hulkdesign.com)
resource customDomain 'Microsoft.Web/staticSites/customDomains@2023-12-01' = if (!empty(customDomainName)) {
  parent: staticWebApp
  name: customDomainName
  properties: {}
}

output name string = staticWebApp.name
output uri string = 'https://${staticWebApp.properties.defaultHostname}'
output defaultHostname string = staticWebApp.properties.defaultHostname
output id string = staticWebApp.id
