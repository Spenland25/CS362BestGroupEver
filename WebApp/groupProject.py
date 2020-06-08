#   Mason Davis
#   CS 362 Spring 2020
#   Group Project
#
#   This program makes use of basic HTML and flask to create a simple
#   interface for a user to interact with in multiple different ways. The
#   foundations of this program is to imitate a virus tracker, and allow the
#   user to create accounts/login, enter in details, and get a report on their
#   probability of infection



import mysql.connector
from flask import Flask, render_template, request, flash, redirect, request, session, abort, url_for
from Graph import Graph
app = Flask(__name__)

USERNAME = ""
USERID = 0


# The main page which displays the login/create account buttons
@app.route('/')
def home():
    return render_template('home.html')



# The create account page allows a user to enter in a username and a password.
# When they click the 'create account' button, the information is inserted
# into the local database accordingly
@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():
    # if 'create account' button is pressed
    if "createAccount" in request.form:
        message = "ACCOUNT CREATED SUCCESSFULLY"

        # grab username and password info the user entered
        username = request.form.get('username')
        password = request.form.get('password')
        
        # if the text fields were not left blank
        if username != '' or password != '':
            cnx = mysql.connector.connect(user='root', password='Hoover96',
                                    host='localhost',
                                    database='groupProject')


            cursor = cnx.cursor()

            query = "INSERT into user (userName, password) values (%s, %s)"
            values = (username, password)

            cursor.execute(query, values)

            cnx.commit()

            cursor.close()
            cnx.close()
            return render_template('createAccount.html', message=message)
        # if they were, display message and reload page for re-entry
        else:
            message = "INVALID CREDENTIALS"
            return render_template('createAccount.html', message=message)
    else:
        pass

    return render_template('createAccount.html')



# The login page allows the user to enter in their username and password. The
# information is checked against the database to ensure the user already has
# an account.
@app.route('/login', methods=['GET', 'POST'])
def login():
    cnx = mysql.connector.connect(user='root', password='Hoover96',
                              host='localhost',
                              database='groupProject')
                            
    username = request.form.get('username')
    password = request.form.get('password')

    cursor = cnx.cursor()

    query = "SELECT * from user"

    cursor.execute(query)

    records = cursor.fetchall()

    # start checking through the database, see if username/password exists
    for row in records:
        userid = row[0]
        uname = row[1]
        passwd = row[2]

        error = None
        if request.method == 'POST':
            # if corresponding name/password is found - allow login
            if request.form['username'] == uname and request.form['password'] == passwd:
                global USERNAME
                USERNAME = username
                global USERID
                USERID = userid
                # if admin, send to separate page
                if request.form['username'] == 'admin' and request.form['password'] == 'admin':
                    cursor.close()
                    cnx.close()
                    return redirect(url_for('adminOptions'))   
                else:
                    cursor.close()
                    cnx.close()
                    return redirect(url_for('userOptions'))
            # if info not found, prompt for re-entry
            else:
                error = 'Invalid Credentials. Please try again.'

    return render_template('login.html', error=error)


# displays options the user can select
@app.route('/userOptions', methods=['GET', 'POST'])
def userOptions():
    return render_template('userOptions.html')


# displays options the admin can select
@app.route('/adminOptions', methods=['GET', 'POST'])
def adminOptions():
    return render_template('adminOptions.html')


# admin specific page. allows the admin to assign a specific user to have the
# virus by entering in their username
@app.route('/assignVirus', methods=['GET', 'POST'])
def assignVirus():
    message = "SUCCESSFULLY ASSIGNED"

    if "assignVirus" in request.form:
        username = request.form.get('username')

        if username != '':
            cnx = mysql.connector.connect(user='root', password='Hoover96',
                                    host='localhost',
                                    database='groupProject')

            val = 'YES'

            cursor = cnx.cursor()

            query = "SELECT * from user"

            cursor.execute(query)

            records = cursor.fetchall()

            notValid = True
            for x in records:
                if username != x[1]:
                    continue
                elif username == x[1]:
                    notValid = False
                    break

            if notValid == True:
                message = "INVALID CREDENTIALS" 
                return render_template('assignVirus.html', message=message)
            else:

                query = "UPDATE user set infected = (%s) where username = (%s)"
                values = (val, username)

                cursor.execute(query, values)

                cnx.commit()

                cursor.close()
                cnx.close()
                return render_template('assignVirus.html', message=message)
        else:
            message = "INVALID CREDENTIALS"
            return render_template('assignVirus.html', message=message)

    return render_template('assignVirus.html')


# a page that allows the user to enter in a location and visit date that is
# associated with their information. This info will be used to determine
# infection probability
@app.route('/enterDetails', methods=['GET', 'POST'])
def enterDetails():
    message = "DETAILS ENTERED SUCCESSFULLY"

    if "submitDetails" in request.form:

        location = request.form.get('location')
        date = request.form.get('date')
        time = request.form.get('time')

        if location != '' or date != None or time != None:
            cnx = mysql.connector.connect(user='root', password='Hoover96',
                                    host='localhost',
                                    database='groupProject')

            time = time + ":00"

            cursor = cnx.cursor()

            query = "SELECT * from user where username = (%s)"
            value = (USERNAME)

            cursor.execute(query, (value,))

            records = cursor.fetchall()

            # grab userId of current user
            for x in records:
                userId = x[0]


            query = "SELECT * from location where name = (%s)"
            value = (location)

            cursor.execute(query, (value,))

            records = cursor.fetchall()

            # grab locationID for location being selected by user
            for x in records:
                locationId = x[0]

            # insert info that the user selected, and make it associated with
            # their account information
            query = "INSERT into survey (uID, lID, visitDate, visitTime) values (%s, %s, %s, %s)"
            values = (userId, locationId, date, time)


            cursor.execute(query, values)

            cnx.commit()

            cursor.close()
            cnx.close()

            return render_template('enterDetails.html', message=message)
        else:
            message = "INVALID INFORMATION"
            return render_template('enterDetails.html', message=message)

    return render_template('enterDetails.html')


# the get report page allows a user to select a specific date that they want
# to use in order to determine their probability of infection. It will be
# using a graph and Dijkstra's algorithm (slightly modified to return the edge
# weights, rather than the node path)
@app.route('/getReport', methods=['GET', 'POST'])
def getReport():
    message = ""
    infectionStatus = "NO"
    infectedPerson = 0
    emptySet = False


    if "submitDetails" in request.form:
        date = request.form.get('date')
        cnx = mysql.connector.connect(user='root', password='Hoover96',
                                host='localhost',
                                database='groupProject')

        cursor = cnx.cursor()

        # select all people who have been to any location within the certain day
        # that the user selected
        query = "SELECT survey.uID, survey.lID, location.transmitPercentage, user.infected from survey join user on user.userID = survey.uID join location on location.locationID = survey.lID where survey.visitDate = (%s)"
        value = (date)

        cursor.execute(query, (date,))

        #cnx.commit()

        records = cursor.fetchall()

        # if no results from query, report back immediately
        if cursor.rowcount == 0:
                message = "0%"
                return render_template('getReport.html', message=message)

        # determine if an infected person is within the group of people
        for x in records:
            infectionStatus = x[3]
            if infectionStatus == "YES":
                infectedPerson = x[0]   # save the infected persons ID
                break  

        # if no infected person, report back immediately
        if infectionStatus == "NO":
            message = "0%"
            return render_template('getReport.html', message=message)

        # if infected person is the user
        elif infectedPerson == USERID:
            message = "100%"
            return render_template('getReport.html', message=message)

        # begin determining probability of infection for user       
        else:

            # first table will be used to iterate through user ID's to have a
            # 'vertex 1' which will be connected to a vertex 2 later
            query = "SELECT survey.uID, survey.lID, location.transmitPercentage from survey join user on user.userID = survey.uID join location on location.locationID = survey.lID where survey.visitDate = (%s)"
            value = (date)

            cursor.execute(query, (date,))


            allLocationsRecords = cursor.fetchall()

            graph = Graph()

            # first loop will iterate though, saving the userID as 'Vertex1'
            for i in allLocationsRecords:
                vertex1 = str(i[0])
                location = i[1]

                # query to get the table of people who are linked by location
                query = "SELECT survey.uID, survey.lID, location.transmitPercentage from survey join user on user.userID = survey.uID join location on location.locationID = survey.lID where survey.visitDate = (%s) and survey.lID = (%s)"
                values = (date, location)

                cursor.execute(query, values)

                oneLocationRecords = cursor.fetchall()

                # second loop will iterate through, saving the userID as
                # 'Vertex2' and the weight associated with that location.
                # Connects the vertices
                for j in oneLocationRecords:
                    vertex2 = str(j[0])
                    weight = str(j[2])

                    # don't connect a node to itself
                    if vertex1 == vertex2:
                        continue
                    else:
                        graph.add_edge(vertex1, vertex2, weight)

            # get edge weights of shortest path from infected person to user
            edgeWeights = dijsktra(graph, str(infectedPerson), str(USERID))

            # weights are returned in reverse order - fixed it
            edgeWeights.reverse()

            # converted to int
            edgeWeights = [int(i) for i in edgeWeights]

            probability = 1.0

            # go through edgeweights and calculate the overall probability
            for x in range(len(edgeWeights)):
                probability = probability * edgeWeights[x]

            # if user is not directly connected to infected person
            if len(edgeWeights) > 1:
                probability = float(probability / 100)
            else:
                probability = edgeWeights[0]
            probability = str(probability) + "%"

            message = probability
            return render_template('getReport.html', message=message)

        cursor.close()
        cnx.close()

    return render_template('getReport.html', message=message)


# gotten from the internet and slightly modified to return edge weights as
# opposed to the node path from one vertex to another
# https://benalexkeen.com/implementing-djikstras-shortest-path-algorithm-with-python/
def dijsktra(graph, initial, end):
    # shortest paths is a dict of nodes
    # whose value is a tuple of (previous node, weight)
    shortest_paths = {initial: (None, 0)}
    current_node = initial
    visited = set()

    edgeWeights = []
    
    while current_node != end:
        visited.add(current_node)
        destinations = graph.edges[current_node]
        weight_to_current_node = shortest_paths[current_node][1]

        for next_node in destinations:
            weight = int(graph.weights[(current_node, next_node)]) + weight_to_current_node
            if next_node not in shortest_paths:
                shortest_paths[next_node] = (current_node, weight)
            else:
                current_shortest_weight = shortest_paths[next_node][1]
                if current_shortest_weight > weight:
                    shortest_paths[next_node] = (current_node, weight)
        
        next_destinations = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
        if not next_destinations:
            return "Route Not Possible"
        # next node is the destination with the lowest weight
        current_node = min(next_destinations, key=lambda k: next_destinations[k][1])
    
    # Work back through destinations in shortest path
    path = []
    while current_node is not None:
        path.append(current_node)
        next_node = shortest_paths[current_node][0]
        if next_node != None:
            edgeWeights.append(graph.weights[(current_node, next_node)])
        else:
            pass
        current_node = next_node
    # Reverse path
    path = path[::-1]
    #return path
    return edgeWeights



if __name__ == '__main__':
    app.run()
    #app.secret_key = os.urandom(12)
    #app.run(debug=True,host='0.0.0.0', port=4000)

#main()