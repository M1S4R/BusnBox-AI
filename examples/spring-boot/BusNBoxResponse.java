package com.company.travel.busnbox;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Public response model returned by BusNBox AI to Spring Boot.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class BusNBoxResponse {

    @JsonProperty("success")
    private boolean success;

    @JsonProperty("response_id")
    private String responseId;

    @JsonProperty("conversation_id")
    private String conversationId;

    @JsonProperty("intent")
    private String intent;

    @JsonProperty("reply")
    private String reply;

    @JsonProperty("parameters")
    private Map<String, Object> parameters;

    @JsonProperty("trips")
    private List<Map<String, Object>> trips = Collections.emptyList();

    @JsonProperty("suggestions")
    private List<Map<String, Object>> suggestions = Collections.emptyList();

    @JsonProperty("recommendations")
    private List<Map<String, Object>> recommendations = Collections.emptyList();

    @JsonProperty("error")
    private ErrorDetail error;

    @JsonProperty("detail")
    private String detail;

    public static class ErrorDetail {
        @JsonProperty("code")
        private String code;

        @JsonProperty("message")
        private String message;

        public String getCode() {
            return code;
        }

        public void setCode(String code) {
            this.code = code;
        }

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }
    }

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getResponseId() {
        return responseId;
    }

    public void setResponseId(String responseId) {
        this.responseId = responseId;
    }

    public String getConversationId() {
        return conversationId;
    }

    public void setConversationId(String conversationId) {
        this.conversationId = conversationId;
    }

    public String getIntent() {
        return intent;
    }

    public void setIntent(String intent) {
        this.intent = intent;
    }

    public String getReply() {
        return reply;
    }

    public void setReply(String reply) {
        this.reply = reply;
    }

    public Map<String, Object> getParameters() {
        return parameters;
    }

    public void setParameters(Map<String, Object> parameters) {
        this.parameters = parameters;
    }

    public List<Map<String, Object>> getTrips() {
        return trips;
    }

    public void setTrips(List<Map<String, Object>> trips) {
        this.trips = trips;
    }

    public List<Map<String, Object>> getSuggestions() {
        return suggestions;
    }

    public void setSuggestions(List<Map<String, Object>> suggestions) {
        this.suggestions = suggestions;
    }

    public List<Map<String, Object>> getRecommendations() {
        return recommendations;
    }

    public void setRecommendations(List<Map<String, Object>> recommendations) {
        this.recommendations = recommendations;
    }

    public ErrorDetail getError() {
        return error;
    }

    public void setError(ErrorDetail error) {
        this.error = error;
    }

    public String getDetail() {
        return detail;
    }

    public void setDetail(String detail) {
        this.detail = detail;
    }
}
