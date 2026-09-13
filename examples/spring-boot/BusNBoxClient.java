package com.company.travel.busnbox;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;

/**
 * Production-ready reference client for integrating the BusNBox AI module into Spring Boot.
 *
 * Handles:
 * - Base URL configuration via BusNBoxProperties
 * - Configurable request timeout
 * - Optional service-to-service API key header
 * - Structured error mapping without throwing unhandled exceptions
 */
@Service
public class BusNBoxClient {

    private final WebClient webClient;
    private final Duration timeout;

    public BusNBoxClient(BusNBoxProperties properties, WebClient.Builder webClientBuilder) {
        this.timeout = properties.getTimeout();

        WebClient.Builder builder = webClientBuilder
                .baseUrl(properties.getBaseUrl())
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE);

        if (properties.getApiKey() != null && !properties.getApiKey().isBlank()) {
            builder.defaultHeader("X-BusNBox-Key", properties.getApiKey());
        }

        this.webClient = builder.build();
    }

    /**
     * Sends a natural language chat message to the BusNBox AI module.
     *
     * @param message User's input text (e.g., "Find buses from Chennai to Bangalore tomorrow")
     * @param conversationId Unique session ID (owned by the company application)
     * @return Mono of BusNBoxResponse with extracted intent, parameters, trips, and reply
     */
    public Mono<BusNBoxResponse> chat(String message, String conversationId) {
        BusNBoxRequest request = new BusNBoxRequest(message, conversationId);

        return this.webClient.post()
                .uri("/api/v1/chat")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(BusNBoxResponse.class)
                .timeout(this.timeout)
                .onErrorResume(WebClientResponseException.class, ex -> {
                    // Map HTTP 4xx/5xx responses into the standardized BusNBoxResponse error model
                    try {
                        BusNBoxResponse errorBody = ex.getResponseBodyAs(BusNBoxResponse.class);
                        if (errorBody != null) {
                            return Mono.just(errorBody);
                        }
                    } catch (Exception ignored) {
                    }

                    BusNBoxResponse fallback = new BusNBoxResponse();
                    fallback.setSuccess(false);
                    BusNBoxResponse.ErrorDetail err = new BusNBoxResponse.ErrorDetail();
                    err.setCode("UPSTREAM_ERROR_" + ex.getStatusCode().value());
                    err.setMessage(ex.getMessage());
                    fallback.setError(err);
                    return Mono.just(fallback);
                })
                .onErrorResume(java.util.concurrent.TimeoutException.class, ex -> {
                    BusNBoxResponse timeoutResponse = new BusNBoxResponse();
                    timeoutResponse.setSuccess(false);
                    BusNBoxResponse.ErrorDetail err = new BusNBoxResponse.ErrorDetail();
                    err.setCode("TIMEOUT");
                    err.setMessage("BusNBox AI did not respond within the configured timeout (" + this.timeout.toSeconds() + "s).");
                    timeoutResponse.setError(err);
                    return Mono.just(timeoutResponse);
                });
    }

    /**
     * Checks liveness of the BusNBox AI module.
     *
     * @return Mono of Boolean indicating whether the service is alive
     */
    public Mono<Boolean> checkHealth() {
        return this.webClient.get()
                .uri("/api/v1/health")
                .retrieve()
                .toBodilessEntity()
                .map(entity -> entity.getStatusCode().is2xxSuccessful())
                .onErrorReturn(false);
    }
}
