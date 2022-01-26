<!--
 Copyright 2020 BigBitBus

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

<template>
	<div>
		<head>
			<title>TodoMVC</title>
			<link
				rel="stylesheet"
				type="text/css"
				href="https://unpkg.com/todomvc-app-css@2.2.0/index.css"
			/>
		</head>
		<body>
			<section class="todoapp">
				<header class="header">
					<h1>todos</h1>
					<input
						class="new-todo"
						autofocus
						autocomplete="off"
						placeholder="Lets get going, shall we?"
						v-model="title"
						@keyup.enter="postTodo"
					/>
				</header>

				<section class="main" v-show="todos.length" v-cloak>
					<input id="toggle-all" class="toggle-all" type="checkbox" />
					<label for="toggle-all"></label>
					<ul class="todo-list">
						<li
							v-for="todo in todos"
							class="todo"
							:key="todo.id"
							:class="{ completed: todo.completed, editing: todo == editedTodo }"
						>
							<div class="view">
								<input class="toggle" type="checkbox" v-model="todo.completed" />
								<label @dblclick="editTodo(todo)">{{ todo.title }}</label>
								<button class="destroy" @click="deleteTodo(todo)"></button>
							</div>

							<input
								class="edit"
								type="text"
								v-model="todo.title"
								v-todo-focus="todo == editedTodo"
								@blur="doneEdit(todo)"
								@keyup.enter="doneEdit(todo)"
								@keyup.esc="cancelEdit(todo)"
							/>
						</li>
					</ul>
				</section>
			</section>
		</body>
		<!--
    <div class="columns">
      <div>
        <div class="todo">
          <div class="card" v-for="task in tasks" v-bind:key="task.id">
            <div class="card-content">{{ task.title}}</div>
          </div>
        </div>
      </div>
    </div>
    -->
	</div>
</template>

<script>
import axios from "axios";
const api_server_endpoint = process.env.VUE_APP_DJANGO_ENDPOINT;
var URL = `${api_server_endpoint}/djangoapi/apis/v1/`;
export default {
	name: "App",
	data() {
		return {
			todos: [],
			title: "",
			editedTodo: null
		};
	},
	mounted() {
		this.getTodo();
	},
	methods: {
		getTodo() {
			axios({
				method: "GET",
				url: URL
			})
				.then(response => (this.todos = response.data))
				.catch(error => {
					console.error("Error:", error);
				});
		},
		postTodo() {
			var d = new Date();
			var month = d.getMonth() + 1;
			var year = d.getFullYear();
			var date = d.getDate();
			axios({
				method: "POST",
				url: URL,
				data: {
					title: this.title,
					description: month + " " + date + " " + year
				}
			})
				.then(response => {
					this.todos.push({
						id: response.data.id,
						title: this.title,
						description: month + " " + date + " " + year
					});
					//reset
					this.title = "";
				})
				.catch(error => {
					console.error("Error:", error);
				});
		},

		deleteTodo(todo) {
			var id = todo.id;
			axios({
				method: "DELETE",
				url: URL + id
			}).catch(error => {
				console.error("Error:", error);
			});
			for (var i = 0; i < this.todos.length; i++) {
				if (this.todos[i].id == id) {
					this.todos.splice(i, 1);
					break;
				}
			}
		},
		editTodo(todo) {
			this.beforeEditCache = todo.title;
			this.editedTodo = todo;
		},
		doneEdit(todo) {
			var id = todo.id;
			if (!this.editedTodo) {
				return;
			}

			todo.title = this.editedTodo.title.trim();
			axios({
				method: "PUT",
				url: URL + id + "/",
				data: {
					title: this.editedTodo.title,
					description: todo.description
				}
			}).catch(error => {
				console.error("Error:", error);
			});
			this.editedTodo = null;
		},
		cancelEdit(todo) {
			this.editedTodo = null;
			todo.title = this.beforeEditCache;
		}
	}
};
</script>
