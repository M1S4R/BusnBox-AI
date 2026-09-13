package com.company.travel.busnbox;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Public request payload sent from Spring Boot to BusNBox AI.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class BusNBoxRequest {

    @JsonProperty("message")
    private String message;

    @JsonProperty("conversation_id")
    private String conversationId;

    @JsonProperty("tenant_key")
    private String tenantKey = "busnbox";

    public BusNBoxRequest() {
    }

    public BusNBoxRequest(String message, String conversationId) {
        this.message = message;
        this.conversationId = conversationId;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getConversationId() {
        return conversationId;
    }

    public void setConversationId(String conversationId) {
        this.conversationId = conversationId;
    }

    public String getTenantKey() {
        return tenantKey;
    }

    public void setTenantKey(String tenantKey) {
        this.tenantKey = tenantKey;
    }
}
