FROM docker.io/library/golang:1.27.1-alpine3.24@sha256:8a5910f31396cd4d89662f56c68b3ae31d374308270a1c3bd96672ee5ed43414 AS build
ENV CGO_ENABLED=0 GOTOOLCHAIN=local GOMAXPROCS=2
WORKDIR /src
COPY gosu-source.tar /src/gosu-source.tar
RUN echo "cb892cf183914b349fe08cf85d758b4221f8eb9f9b821c2c9c2aca35ff052011  gosu-source.tar" | sha256sum -c - && tar -xf gosu-source.tar && rm gosu-source.tar
RUN go mod download && go mod verify && go test ./... && go build -mod=readonly -trimpath -buildvcs=false -ldflags '-d -w' -o /out/gosu . && go version -m /out/gosu
FROM docker.io/library/postgres:17.11-alpine3.24@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24
COPY --from=build --chmod=0755 /out/gosu /usr/local/bin/gosu
COPY sources.lock.json /usr/local/share/sonar-postgres-sources.json
ARG SOURCE_REVISION
LABEL org.opencontainers.image.source="https://github.com/imos64/sonarqube-kubernetes" org.opencontainers.image.revision=$SOURCE_REVISION \
      org.opencontainers.image.description="PostgreSQL 17.11 Alpine; unchanged gosu 1.19 source rebuilt with fixed Go 1.27.1"
RUN gosu --version && test "$(gosu postgres id -u)" = 70
USER 70:70
