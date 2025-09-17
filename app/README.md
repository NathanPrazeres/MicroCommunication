# Application Layer

This was where the _actual_ code of our application is going to be hosted.

For learning purposes, we chose a language for each Service that was implemented by ourselves.

Those include:

- [User Service](#user-service)

- [Chat Service](#chat-service)

## Structure

Most services had to implement the following layers:

- `api`

- `models`

- `repositories`

- `services`

- `auth`

- `cache`

and an optional `middleware` layer.

## User Service

This was implemented in Rust (if you can't beat them, join them).

Due to it's soaring popularity in the last few months, we used [Axum](https://docs.rs/axum/latest/axum/) for our REST API layer and as our Web framework.

## Chat Service
