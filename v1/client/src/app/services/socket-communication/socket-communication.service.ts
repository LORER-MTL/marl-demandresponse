import { Injectable } from '@angular/core';
import { NotificationService } from '@app/services/notification/notification.service';
import { SocketService } from '@app/services/socket/socket.service';

@Injectable({
  providedIn: 'root'
})
export class SocketCommunicationService {

  constructor(        
    public socketService: SocketService,
    private snackBarService: NotificationService,
  ) { }

  connect(): void {
    if (!this.socketService.isSocketAlive()) {
        this.socketService.connect();
        const timeout = 2000;
        setTimeout(() => {
            if (!this.socketService.isSocketAlive()) {
                const message = 'Error: cannot connect to server';
                const action = '';
                this.snackBarService.openFailureSnackBar(message, action);
            }
        }, timeout);
        this.configureSocket();
    }
  }

  configureSocket() {
    this.socketService.on('connected', () => {
      this.snackBarService.openSuccessSnackBar('Connected to server', '');
    });

    this.socketService.on('pong', () => {
      this.snackBarService.openSuccessSnackBar('Pong from server', '');
    });

    this.socketService.on('dataChange', (data) => {
      console.log(data);
    });
  }

  pingServer() {
    this.socketService.send('connected');
    // this.snackBarService.openSuccessSnackBar('Pinging server...', '');
  }
}
