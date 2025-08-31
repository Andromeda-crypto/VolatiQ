/**
 * K6 Load Test for VolatiQ API
 * Tests API performance under various load conditions
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export let options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp-up to 5 users over 30s
    { duration: '1m', target: 10 },   // Stay at 10 users for 1m
    { duration: '30s', target: 20 },  // Ramp-up to 20 users over 30s
    { duration: '2m', target: 20 },   // Stay at 20 users for 2m
    { duration: '30s', target: 0 },   // Ramp-down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate must be less than 10%
    errors: ['rate<0.1'],             // Custom error rate must be less than 10%
  },
};

// Base URL
const BASE_URL = 'http://localhost:5000';

// Sample features for testing
const sampleFeatures = [
  [0.001, 0.02, 150.5, 149.8, 65.2],
  [0.002, 0.018, 151.0, 150.1, 68.5],
  [-0.001, 0.025, 149.2, 149.5, 45.8],
  [0.0015, 0.022, 152.1, 151.8, 72.3],
  [0.0008, 0.019, 150.8, 150.3, 58.7]
];

export function setup() {
  // Setup function - runs once before all VUs
  console.log('Starting VolatiQ load test...');
  
  // Test that the API is available
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'API is available': (r) => r.status === 200 || r.status === 503,
  });
  
  return { timestamp: new Date().toISOString() };
}

export default function(data) {
  // Main test function - runs for each VU
  
  // Test 1: API Info endpoint
  const infoResponse = http.get(`${BASE_URL}/`);
  check(infoResponse, {
    'API info status is 200': (r) => r.status === 200,
    'API info response time < 200ms': (r) => r.timings.duration < 200,
    'API info has version': (r) => r.json('version') !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: Health check endpoint
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'Health check responds': (r) => r.status === 200 || r.status === 503,
    'Health check response time < 100ms': (r) => r.timings.duration < 100,
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: Prediction endpoint with small batch
  const smallBatch = {
    features: sampleFeatures.slice(0, 2)
  };
  
  const predictResponse = http.post(
    `${BASE_URL}/predict`,
    JSON.stringify(smallBatch),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
  
  const predictSuccess = check(predictResponse, {
    'Predict status is 200 or 500': (r) => r.status === 200 || r.status === 500,
    'Predict response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  if (!predictSuccess) {
    errorRate.add(1);
  }
  
  // If prediction succeeded, check response structure
  if (predictResponse.status === 200) {
    check(predictResponse, {
      'Predict has predictions array': (r) => {
        const json = r.json();
        return Array.isArray(json.predictions);
      },
      'Predict has timestamp': (r) => r.json('timestamp') !== undefined,
      'Predict has correct number of predictions': (r) => {
        const json = r.json();
        return json.predictions && json.predictions.length === 2;
      },
    }) || errorRate.add(1);
  }

  sleep(2);

  // Test 4: Explanation endpoint (less frequent due to computational cost)
  if (Math.random() < 0.3) { // 30% chance to run explanation
    const explainBatch = {
      features: [sampleFeatures[0]]
    };
    
    const explainResponse = http.post(
      `${BASE_URL}/explain`,
      JSON.stringify(explainBatch),
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    const explainSuccess = check(explainResponse, {
      'Explain status is 200 or 500': (r) => r.status === 200 || r.status === 500,
      'Explain response time < 5000ms': (r) => r.timings.duration < 5000,
    });
    
    if (!explainSuccess) {
      errorRate.add(1);
    }
    
    // If explanation succeeded, check response structure
    if (explainResponse.status === 200) {
      check(explainResponse, {
        'Explain has SHAP values': (r) => {
          const json = r.json();
          return Array.isArray(json.shap_values);
        },
        'Explain has feature names': (r) => {
          const json = r.json();
          return Array.isArray(json.feature_names) && json.feature_names.length === 5;
        },
      }) || errorRate.add(1);
    }
    
    sleep(3);
  }

  // Test 5: Metrics endpoint (occasional check)
  if (Math.random() < 0.2) { // 20% chance
    const metricsResponse = http.get(`${BASE_URL}/metrics`);
    check(metricsResponse, {
      'Metrics status is 200': (r) => r.status === 200,
      'Metrics response time < 500ms': (r) => r.timings.duration < 500,
      'Metrics has model info': (r) => r.json('model_info') !== undefined,
    }) || errorRate.add(1);
    
    sleep(1);
  }

  // Test 6: Error handling
  if (Math.random() < 0.1) { // 10% chance to test error cases
    // Test invalid prediction request
    const invalidRequest = {
      features: [[1, 2, 3]] // Wrong number of features
    };
    
    const errorResponse = http.post(
      `${BASE_URL}/predict`,
      JSON.stringify(invalidRequest),
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    check(errorResponse, {
      'Invalid request returns 400': (r) => r.status === 400,
      'Error response has error field': (r) => r.json('error') !== undefined,
    }) || errorRate.add(1);
  }

  // Random sleep to simulate realistic user behavior
  sleep(Math.random() * 2 + 1); // Sleep 1-3 seconds
}

export function teardown(data) {
  // Teardown function - runs once after all VUs complete
  console.log('Load test completed at:', new Date().toISOString());
  console.log('Test started at:', data.timestamp);
}
