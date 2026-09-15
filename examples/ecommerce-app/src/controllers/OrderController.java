package com.example.ecommerce.controllers;

import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    public record OrderSummary(String orderId, double totalAmount, String status) {}

    @GetMapping("/active")
    public List<OrderSummary> getActiveOrders() {
        return List.of(new OrderSummary("ord_101", 89.99, "PROCESSING"));
    }

    @PostMapping("/cancel/{orderId}")
    public void cancelOrder(@PathVariable String orderId) {
        // Business logic to void transaction
    }
}
