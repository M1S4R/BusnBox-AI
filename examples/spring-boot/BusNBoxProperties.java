package com.company.travel.busnbox;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.time.Duration;

/**
 * Configuration properties for the BusNBox AI module.
 *
 * Example application.yml configuration:
 * <pre>
 * busnbox:
 *   base-url: ${BUSNBOX_BASE_URL:http://localhost:8000}
 *   timeout: ${BUSNBOX_TIMEOUT:10s}
 *   api-key: ${BUSNBOX_API_KEY:}
 * </pre>
 */
@Component
@ConfigurationProperties(prefix = "busnbox")
public class BusNBoxProperties {

    /**
     * Base URL where the BusNBox AI FastAPI service is deployed.
     * Default: http://localhost:8000
     */
    private String baseUrl = "http://localhost:8000";

    /**
     * HTTP request timeout for communication with BusNBox AI.
     * Default: 10 seconds
     */
    private Duration timeout = Duration.ofSeconds(10);

    /**
     * Optional service-to-service API key for secure private communication.
     */
    private String apiKey = "";

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public Duration getTimeout() {
        return timeout;
    }

    public void setTimeout(Duration timeout) {
        this.timeout = timeout;
    }

    public String getApiKey() {
        return apiKey;
    }

    public void setApiKey(String apiKey) {
        this.apiKey = apiKey;
    }
}
