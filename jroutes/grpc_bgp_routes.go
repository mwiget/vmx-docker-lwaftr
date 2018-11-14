package main

import (
	"context"
	"io/ioutil"
	"log"
	"strconv"
	"strings"

	"google.golang.org/grpc"

	authentication "github.com/juniper/vmx-docker-lwaftr/jroutes/stubs/authentication"
	routing "github.com/juniper/vmx-docker-lwaftr/jroutes/stubs/routing"
)

// GrpcSession contains gRPC connection handle
type GrpcSession struct {
	conn *grpc.ClientConn
	cbgp *routing.BgpRouteClient
}

// GrpcDial opens gRPC session to host
func (g *GrpcSession) GrpcDial(host *string, grpcPort int, user *string, id *string) bool {

	var opts []grpc.DialOption

	log.SetFlags(log.LstdFlags)

	pwd, err := ioutil.ReadFile("." + *host + ".pwd")
	if err != nil {
		log.Fatalf("password file missing: ." + *host + ".pwd")
		return (false)
	}
	pwdStr := strings.TrimSuffix(string(pwd), "\r\n")

	hostname := *host + ":" + strconv.Itoa(grpcPort)

	opts = append(opts, grpc.WithInsecure())
	conn, err := grpc.Dial(hostname, opts...)
	if err != nil {
		log.Fatalf("Could not connect via gRPC to %s: %s", hostname, err)
		return (false)
	}
	g.conn = conn

	l := authentication.NewLoginClient(g.conn)
	dat, err := l.LoginCheck(context.Background(),
		&authentication.LoginRequest{UserName: *user, Password: pwdStr, ClientId: *id})

	if err != nil {
		log.Fatalf("Authentication failed for user %s with password %s: %s", *user, pwdStr, err)
		return (false)
	}
	log.Printf("gRPC authenticated to %s as %s", hostname, *user)

	c := routing.NewBgpRouteClient(g.conn)

	var bgpRouteInit routing.BgpRouteInitializeRequest
	_, err = c.BgpRouteInitialize(context.Background(), &bgpRouteInit)
	if err != nil {
		log.Fatalf("BGP route service initialization failed: %s", err)
		return (false)
	}

	g.cbgp = &c
	log.Println("BGP route service initialized.")

	return dat.Result
}
