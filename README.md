# project_573
Name: Pinxiang Wang \
Unity ID: pwang25 \
Command to Run the server: \
![img.png](img.png)
Command to Run the client: \
![img_1.png](img_1.png)

In the project, I use 2 new threads to block any future connection in the seller setup statge
and out number buyer connection stage. 

When you start a normal client when the seller connection has built up, it supposed to be assigned
as a buyer, however since the independent blocking thread has content not flushing, it would suggeset
as 'Server is busy, please try again later.'

It will not influence the future behavior of this system just restart the client using the command above
again, and it will work normally.

![img_3.png](img_3.png)

![img_2.png](img_2.png)

![img_4.png](img_4.png)

![img_5.png](img_5.png)

![img_6.png](img_6.png)

![img_7.png](img_7.png)

Biding Finished:
![img_8.png](img_8.png)