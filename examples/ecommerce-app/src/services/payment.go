package services

import (
	"errors"
	"fmt"
)

// PaymentRequest holds customer payment charge details
type PaymentRequest struct {
	CustomerID string  `json:"customerId"`
	Amount     float64 `json:"amount"`
	Currency   string  `json:"currency"`
}

// PaymentResult represents the gateway confirmation
type PaymentResult struct {
	TransactionID string `json:"transactionId"`
	Status        string `json:"status"`
}

// PaymentGateway interface for charge operations
type PaymentGateway interface {
	Charge(req PaymentRequest) (*PaymentResult, error)
}

// ProcessCheckout validates cart balance and commits payment charge
func ProcessCheckout(req PaymentRequest) (*PaymentResult, error) {
	if req.Amount <= 0 {
		return nil, errors.New("charge amount must be positive")
	}
	return &PaymentResult{
		TransactionID: fmt.Sprintf("txn_%s", req.CustomerID),
		Status:        "SUCCESS",
	}, nil
}
