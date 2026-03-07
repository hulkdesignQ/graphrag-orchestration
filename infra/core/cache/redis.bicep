@description('Azure Managed Redis instance name')
param cacheName string

@description('Location for the Redis instance')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {}

@description('Enable high availability (two-node replication)')
param highAvailability bool = true

// Azure Managed Redis cluster (Balanced B0 — 500 MB, 2 vCPUs)
resource redisCluster 'Microsoft.Cache/redisEnterprise@2025-04-01' = {
  name: cacheName
  location: location
  tags: tags
  sku: {
    name: 'Balanced_B0'
  }
  properties: {
    minimumTlsVersion: '1.2'
    highAvailability: highAvailability ? 'Enabled' : 'Disabled'
  }
}

// Database (Azure Managed Redis requires exactly one database named 'default')
resource redisDatabase 'Microsoft.Cache/redisEnterprise/databases@2025-04-01' = {
  name: 'default'
  parent: redisCluster
  properties: {
    clientProtocol: 'Encrypted'
    accessKeysAuthentication: 'Enabled'
    port: 10000
    clusteringPolicy: 'EnterpriseCluster'
    evictionPolicy: 'AllKeysLRU'
  }
}

// Outputs
output redisCacheName string = redisCluster.name
output redisHostName string = redisCluster.properties.hostName
output redisPort int = redisDatabase.properties.port
output redisPrimaryKey string = redisDatabase.listKeys().primaryKey
