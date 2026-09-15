pub struct SessionToken {
    pub token_id: String,
    pub user_id: u64,
    pub expires_at: i64,
}

pub enum AccessRole {
    Customer,
    Merchant,
    Administrator,
}

pub fn verify_session(token: &SessionToken) -> bool {
    token.expires_at > 0
}
