FROM golang:alpine
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o dashboard main.go
EXPOSE 4000
CMD ["./dashboard"]
