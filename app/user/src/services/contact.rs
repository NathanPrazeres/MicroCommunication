use crate::{
    error::{AppError, Result},
    models::{AddContactRequest, UpdateContactRequest, UserContact, UserResponse},
    repositories::ContactRepository,
};
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct ContactService {
    repository: ContactRepository,
}

impl ContactService {
    pub fn new(repository: ContactRepository) -> Self {
        Self { repository }
    }

    /// Create a new contact
    pub async fn create_contact(
        &self,
        user_id: Uuid,
        request: AddContactRequest,
    ) -> Result<UserContact> {
        if user_id == request.contact_id {
            return Err(AppError::BadRequest(
                "Cannot add yourself as a contact".to_string(),
            ));
        }
        let contact = self.repository.create_contact(user_id, request).await?;

        tracing::info!(
            "Created contact {} for user {}",
            contact.contact_id,
            user_id
        );

        Ok(contact)
    }

    /// Get contact by ID
    pub async fn get_contacts(&self, id: Uuid) -> Result<Vec<UserContact>> {
        let contacts = self.repository.get_contacts(id).await?;

        Ok(contacts)
    }

    pub async fn get_contacts_with_profiles(&self, user_id: &Uuid) -> Result<Vec<UserResponse>> {
        let contacts = self.repository.get_contacts_with_profiles(user_id).await?;

        Ok(contacts)
    }

    /// Update contact information
    pub async fn update_contact(
        &self,
        user_id: Uuid,
        contact_id: Uuid,
        request: UpdateContactRequest,
    ) -> Result<UserContact> {
        let contact = self
            .repository
            .update_contact(user_id, contact_id, request)
            .await?;

        tracing::info!("Updated {}'s contact: {}", user_id, contact_id);

        Ok(contact)
    }

    /// Delete user
    pub async fn delete_contact(&self, user_id: Uuid, contact_id: Uuid) -> Result<()> {
        let _: () = self.repository.remove_contact(user_id, contact_id).await?;

        tracing::info!("Deleted {}'s contact: {}", user_id, contact_id);

        Ok(())
    }

    pub async fn get_favorites(&self, user_id: &Uuid) -> Result<Vec<UserContact>> {
        let favorites = self.repository.get_favorites(user_id).await?;

        Ok(favorites)
    }

    pub async fn toggle_favorite(
        &self,
        user_id: &Uuid,
        contact_user_id: &Uuid,
    ) -> Result<UserResponse> {
        let contact = self
            .repository
            .toggle_favorite(user_id, contact_user_id)
            .await?;

        Ok(contact)
    }

    pub async fn get_blocked(&self, user_id: &Uuid) -> Result<Vec<UserContact>> {
        let blocked = self.repository.get_blocked(user_id).await?;

        Ok(blocked)
    }

    pub async fn block_contact(&self, user_id: &Uuid, contact_user_id: &Uuid) -> Result<()> {
        let _ = self
            .repository
            .set_blocked(user_id, contact_user_id, true)
            .await;

        Ok(())
    }

    pub async fn unblock_contact(&self, user_id: &Uuid, contact_user_id: &Uuid) -> Result<()> {
        let _ = self
            .repository
            .set_blocked(user_id, contact_user_id, false)
            .await;

        Ok(())
    }

    pub async fn is_contact(&self, user_id: &Uuid, contact_user_id: &Uuid) -> Result<bool> {
        let exists = self
            .repository
            .contact_exists_for_user(user_id, contact_user_id)
            .await
            .unwrap();

        Ok(exists)
    }
}
